package com.example.deathstarmobileapp

import android.content.ContentValues
import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.os.Bundle
import android.os.Environment
import android.provider.MediaStore
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.Image
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.grid.GridCells
import androidx.compose.foundation.lazy.grid.LazyVerticalGrid
import androidx.compose.foundation.lazy.grid.items
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.Dp
import com.example.deathstarmobileapp.ui.theme.DeathStarMobileAppTheme
import java.io.OutputStream

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            DeathStarMobileAppTheme {
                Surface(
                    modifier = Modifier.fillMaxSize(),
                    color = MaterialTheme.colorScheme.background
                ) {
                    ImageGrid() //displays 10 images
                }
            }
        }
    }
}

@Composable
fun ImageGrid() { //method for displaying the 10 images
    val context = LocalContext.current

    val images = listOf(        //change these "deathstar1" with name of cropped image
        R.drawable.deathstar1,
        R.drawable.deathstar2,
        R.drawable.deathstar3,
        R.drawable.deathstar1,
        R.drawable.deathstar2,
        R.drawable.deathstar3,
        R.drawable.deathstar1,
        R.drawable.deathstar2,
        R.drawable.deathstar3,
        R.drawable.deathstar1
    )

    LazyVerticalGrid(                           //formats the images
        columns = GridCells.Fixed(1),
        modifier = Modifier
            .fillMaxSize()
            .padding(3.dp),
        contentPadding = PaddingValues(3.dp),
        verticalArrangement = Arrangement.spacedBy(8.dp),
        horizontalArrangement = Arrangement.spacedBy(8.dp)
    ) {
        items(images) { imageRes ->
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(2.dp)
                    .border(
                        width = 5.dp,
                        color = Color.Black,
                        shape = MaterialTheme.shapes.medium
                    )
                    .padding(8.dp)
            ) {
                Column {
                    Image(
                        painter = painterResource(id = imageRes),
                        contentDescription = null,
                        modifier = Modifier
                            .aspectRatio(1f)
                            .fillMaxWidth(),
                        contentScale = ContentScale.Crop
                    )
                    Button( //creates download button
                        onClick = {
                            saveImageToGallery(context, imageRes)
                        },
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(top = 1.dp)
                            .padding(bottom = 8.dp),
                        colors = ButtonDefaults.buttonColors(
                            containerColor = Color.Black,
                            contentColor = Color.White
                        )
                    ) {
                        Text("Download")
                    }
                }
            }
        }
    }
}








// method to save drawable resource to a folder on the phone
fun saveImageToGallery(context: Context, drawableResId: Int) {
    val bitmap = BitmapFactory.decodeResource(context.resources, drawableResId)
    val filename = "deathstar_${System.currentTimeMillis()}.jpg"
    val mimeType = "image/jpeg"
    val relativeLocation = Environment.DIRECTORY_PICTURES + "/DeathStarImages"

    val contentValues = ContentValues().apply {
        put(MediaStore.MediaColumns.DISPLAY_NAME, filename)
        put(MediaStore.MediaColumns.MIME_TYPE, mimeType)
        put(MediaStore.MediaColumns.RELATIVE_PATH, relativeLocation)
    }
    val contentResolver = context.contentResolver
    val uri = contentResolver.insert(MediaStore.Images.Media.EXTERNAL_CONTENT_URI, contentValues)

    uri?.let {
        val outputStream: OutputStream? = contentResolver.openOutputStream(it)
        outputStream.use { stream ->
            stream?.let { it1 ->
                if (bitmap.compress(Bitmap.CompressFormat.JPEG, 100, it1)) {
                    Toast.makeText(context, "Image downloaded", Toast.LENGTH_SHORT).show()
                } else {
                    Toast.makeText(context, "Failed to download", Toast.LENGTH_SHORT).show()
                }
            }
        }
    } ?: Toast.makeText(context, "Could not create file", Toast.LENGTH_SHORT).show()
}
